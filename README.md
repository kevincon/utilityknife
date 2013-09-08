UtilityKnife
=========
![Animated GIF demo](/static/images/demo.gif "Animated GIF demo")
UtilityKnife is a web application that visualizes a user's Dropbox space usage/allocation as a treemap. It is similar to desktop programs like Windirstat, KDirStat, Disk Inventory X, Grand Perspective, and Space Monger.

UtilityKnife was built in under 40 hours by Kevin Conley and Carolynn Sullivan at the PennApps Fall 2013 hackathon.

### Inspiration
UtilityKnife's visualization using the treemap from D3.js was heavily inspired by Ben Garvey's Philadelphia budget visualization web application: http://budget.brettmandel.com/

### Getting started

#### Prerequisites
* Python 2.6
* pip
* virtualenv

#### Virtualenv
After cloning the repository, create a virtualenv called "venv" and activate it:
```
virtualenv venv
. venv/bin/activate
```

Then use the requirements.txt file to install the requirements for the app:
```
pip install -r requirements.txt
```

#### Environment Variables
There are several important environment variables that must be defined for the app to work. These are listed in "secrets.py", and it is helpful when working locally to define them in a file called ".env" that foreman will load automatically:

".env"
```
DROPBOX_APP_KEY=fill_me_in
DROPBOX_APP_SECRET=fill_me_in
DROPBOX_APP_REDIRECT=fill_me_in
FLASK_SECRET_KEY=fill_me_in
```

Likewise, it is important to define these environment variables for the production server (i.e. Heroku).

#### Running the App
Start the app with:
```
foreman start
```

If all goes well, you should be able to access the app locally at 127.0.0.1:5000.

### License
```
The MIT License (MIT)

Copyright (c) 2013 Kevin Conley

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```



