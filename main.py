# Main function where I will start app from

from Website import create_app

print("Creating app...")
app = create_app()

if __name__ == '__main__': #If conditional makes sure we do not run it on accident 
    print("App is running..")
    app.run(debug=True)  #Starts flask server
