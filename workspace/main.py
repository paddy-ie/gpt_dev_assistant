try:
    from pizza_app.app import app
except Exception as e:
    print('Failed to import pizza_app:', e)
    print('Make sure files exist under workspace/pizza_app/')
else:
    if __name__ == '__main__':
        print('Starting Pizza Comparison app at http://127.0.0.1:5000')
        app.run(debug=True)
