# Main function where I will start app from
import os
from Website import create_app

print("Creating app...")
app = create_app()

if __name__ == '__main__': #If conditional makes sure we do not run it on accident 
    print("App is running..")
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
