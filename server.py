from typing import Any, Dict, List, Optional, TypedDict
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("icons")

# Iconify API endpoints (with documented backups)
ICONIFY_BASE = "https://api.iconify.design"
ICONIFY_BACKUPS = [
    "https://api.simplesvg.com",
    "https://api.unisvg.com",
]
USER_AGENT = "icon-mcp/1.0"

class SearchResponse(TypedDict, total=False):
    icons: List[str]
    total: int
    limit: int
    start: int
    collections: Dict[str, Any]
    request: Dict[str, str]

async def _request_iconify(
    path: str,
    params: Optional[Dict[str, Any]] = None,
    expect_json: bool = True,
    headers: Optional[Dict[str, str]] = None,
) -> Any | None:
    """Call Iconify API with primary + backup hosts and robust error handling."""
    _headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json" if expect_json else "image/svg+xml",
    }
    if headers:
        _headers.update(headers)

    hosts = [ICONIFY_BASE, *ICONIFY_BACKUPS]
    timeout = httpx.Timeout(30.0)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        last_exc = None
        for host in hosts:
            url = f"{host}{path}"
            try:
                resp = await client.get(url, params=params, headers=_headers)
                resp.raise_for_status()
                return resp.json() if expect_json else resp.text
            except Exception as exc:
                last_exc = exc
                continue
        # all hosts failed
        return None

def _clamp_limit(n: Optional[int]) -> int:
    # Iconify /search: min=32, default=64, max=999
    if n is None:
        return 64
    return max(32, min(999, n))

def _split_icon(icon: str) -> tuple[str, str]:
    # icon format: "prefix:name"
    if ":" not in icon:
        raise ValueError("Icon must be in 'prefix:name' format, e.g., 'mdi:home'")
    prefix, name = icon.split(":", 1)
    if not prefix or not name:
        raise ValueError("Invalid icon, expected 'prefix:name'")
    return prefix, name

@mcp.tool()
async def search_icons(
    query: str,
    limit: Optional[int] = 64,
    start: int = 0,
    prefix: Optional[str] = None,
    prefixes: Optional[List[str]] = None,
    category: Optional[str] = None,
    style: Optional[str] = None,   # "fill" | "stroke"
    palette: Optional[bool] = None # True/False
) -> SearchResponse | str:
    """搜索图标（Iconify /search）。

    Args:
        query: 搜索关键词（支持关键字：style=fill|stroke, palette=true|false）
        limit: 返回条数（32-999）
        start: 分页起始
        prefix: 仅搜索某个图标集前缀
        prefixes: 仅搜索多个图标集前缀（列表）
        category: 仅搜索特定分类的图标集
        style: 过滤笔画风格（fill 或 stroke），将作为关键字附加到 query
        palette: 过滤是否为彩色图标集（True/False），将作为关键字附加到 query
    """
    # 将 style / palette 作为“搜索关键字”附加到 query（Iconify 文档支持）
    # 例如：query="home style=stroke palette=false"
    query_kw = query.strip()
    if style in {"fill", "stroke"}:
        query_kw += f" style={style}"
    if palette is not None:
        query_kw += f" palette={'true' if palette else 'false'}"

    params: Dict[str, Any] = {
        "query": query_kw,
        "limit": _clamp_limit(limit),
        "start": max(0, start),
    }
    if prefix:
        params["prefix"] = prefix
    if prefixes:
        params["prefixes"] = ",".join(prefixes)
    if category:
        params["category"] = category

    data = await _request_iconify("/search", params=params, expect_json=True)
    if not data or "icons" not in data:
        return "Unable to fetch search results or no results found."
    return data  # 直接返回 Iconify 的结构化结果

@mcp.tool()
async def get_svg(
    icon: str,
    color: Optional[str] = None,   # 例: "#ff0000"（注意需 URL encode '#'%23）
    width: Optional[str] = None,   # 例: "24" 或 "24px" 或 "auto"/"unset"/"none"
    height: Optional[str] = None,
    rotate: Optional[str] = None,  # 例: "90deg" 或 "1"(=90deg)/"2"/"3"
    flip: Optional[str] = None,    # "horizontal", "vertical", "horizontal,vertical"
    box: bool = False,
    download: bool = False,
) -> str:
    """获取单个图标的 SVG（Iconify /{prefix}/{name}.svg）。"""
    try:
        prefix, name = _split_icon(icon)
    except ValueError as e:
        return str(e)

    params: Dict[str, Any] = {}
    if color:
        params["color"] = color.replace("#", "%23")
    if width:
        params["width"] = width
    if height:
        params["height"] = height
    if rotate:
        params["rotate"] = rotate
    if flip:
        params["flip"] = flip
    if box:
        params["box"] = 1
    if download:
        params["download"] = 1

    svg = await _request_iconify(f"/{prefix}/{name}.svg", params=params, expect_json=False)
    return svg or "Unable to fetch SVG."

@mcp.tool()
async def get_icon_data(icon: str) -> Dict[str, Any] | str:
    """获取图标数据（Iconify /{prefix}.json?icons=name），返回 IconifyJSON。"""
    try:
        prefix, name = _split_icon(icon)
    except ValueError as e:
        return str(e)

    params = {"icons": name}
    data = await _request_iconify(f"/{prefix}.json", params=params, expect_json=True)
    return data or "Unable to fetch icon data."

@mcp.tool()
async def list_collections(
    prefix: Optional[str] = None,
    prefixes: Optional[List[str]] = None
) -> Dict[str, Any] | str:
    """列出可用图标集（Iconify /collections）。"""
    params: Dict[str, Any] = {}
    if prefix:
        params["prefix"] = prefix
    if prefixes:
        params["prefixes"] = ",".join(prefixes)

    data = await _request_iconify("/collections", params=params, expect_json=True)
    return data or "Unable to fetch collections."

@mcp.tool()
async def list_icons_in_collection(
    prefix: str,
    include_info: bool = False,
    include_chars: bool = False
) -> Dict[str, Any] | str:
    """列出某图标集中的图标（Iconify /collection?prefix=...）。

    Args:
        prefix: 图标集前缀（如 'mdi', 'tabler', 'bi', 'lucide' 等）
        include_info: 是否带上图标集信息
        include_chars: 是否带上字符映射（仅字库导入的集合可用）
    """
    params: Dict[str, Any] = {"prefix": prefix}
    if include_info:
        params["info"] = "1"
    if include_chars:
        params["chars"] = "1"

    data = await _request_iconify("/collection", params=params, expect_json=True)
    return data or f"Unable to fetch icons for collection '{prefix}'."

if __name__ == "__main__":
    # Run the MCP server (stdio / sse / http 均可；此处保持与原示例一致)
    mcp.run(transport="stdio")
