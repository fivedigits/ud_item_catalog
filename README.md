## Prerequisites
The code is supposed to run in Udacity's fullstack vagrant machine. Clone it using
```git clone https://github.com/udacity/fullstack-nanodegree-vm```
You will need VirtualBox and Vagrant. Change into the vagrant directory of the fullstack VM and run
```vagrant up```
This might take a few minutes, if the ubuntu-box is not yet installed on your system. Afterwards, run
```vagrant ssh```
Since oauth2client has been deprecated, you will additionally have to install google-auth and google-auth-oauthlib.
```sudo pip install --upgrade google-auth google-auth-oauthlib```
On
```https://console.developers.google.com/apis/library```
obtain your client-secrets for an application running under port 8000 and place them into
```client_secrets.json```
in the ```catalog``` directory.
