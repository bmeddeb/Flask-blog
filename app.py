from blog_app import create_app

# Create application using factory for CLI and WSGI
app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
