from server import app


if __name__ == "__main__":
    # Run the unified app (IDE at /, classic assistant at /assistant)
    app.run(debug=True, host="127.0.0.1", port=5000)
