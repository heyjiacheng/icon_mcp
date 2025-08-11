# 🚀 Icon MCP Server

This project provides an Icon server for the Model Context Protocol.

## 🛠️ Installation

1.  **Install uv**

    Follow the official instructions to install `uv`:
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

2.  **Clone the repository**

    ```bash
    git clone <repository-url>
    cd icon_mcp
    ```

## ධ Running the Server

Use `uv` to run the server:

```bash
uv run server.py
```

or run with inspetor tool:

```bash
mcp dev server.py 
```

## ⚙️ Cline Configuration

To use this server with Cline, you need to modify your `cline_mcp_setting.json` file. Add or update the `mcpServers` section with the following configuration:

```json
{
  "mcpServers": {
    "icon_mcp": {
      "timeout": 60,
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "/Users/jiadengxu/Documents/code/hackathon/icon_mcp", (use your own path)
        "run",
        "server.py"
      ]
    },
    "github.com/modelcontextprotocol/servers/tree/main/src/filesystem": {
      "autoApprove": [],
      "disabled": false,
      "timeout": 60,
      "type": "stdio",
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/Users/jiadengxu/Documents" (use your own path)
      ]
    }
  }
}
```

## ✨ Example Usage

You can ask Cline the following questions to interact with this server:
```bash
"帮我找支付/付款相关的图标，给出前 10 个候选。从上面里选一个最适合做支付按钮的，并且把 SVG 返回给我。 save the returned SVG file to the `icons` directory here: `/Users/jiadengxu/Documents/code/hackathon/icon_mcp/icons`"
```