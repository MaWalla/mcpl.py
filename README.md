# mcpl.py
Minecraft live player location on [Overviewer](https://overviewer.org/) maps using rcon and WebSockets.

The backend code (main.py) is based on [ArchmageInc/minecraft-player-locations](https://github.com/ArchmageInc/minecraft-player-locations). The client.js is 'borrowed' from there but might be changed later on by me (see TODOs at the end)

-------------
## Usage

First make sure that RCON is enabled on your Minecraft Server.
Do this by making sure that in your `server.properties`:
  - `rcon.port` is set (defaults to `25575` which should be fine)
  - `rcon.password` is set to your preference
  - `enable-rcon` is set to true
  
**WARNING:** With great RCON comes great responsibility! Make sure that your rcon port is properly secured, because intruders may gain a lot of power with this access.

with this set, there are 2 ways for using this script:

### Docker (recommended)

I build and provide Docker images, which can be used here, but you can also build them yourself using the provided Dockerfile.
(Note that next to the mandatory env variables shown here there are also a few optional ones, see below.)
Just use `docker run -p ws_number:ws_number -e RCON_HOST=mcserver_ip -e RCON_PASSWORD=mcrcon_password -e WS_PORT=ws_number mawalla/mcpl.py`

But you can also use docker-compose by using this example docker-compose.yml:

```
version: '3.3'

services:
  mcpl.py:
    image: mawalla/mcpl.py
    ports:
      - "ws_number:ws_number"
    environment:
      - RCON_HOST=mcserver_ip
      - RCON_PASSWORD=mcrcon_password
      - WS_PORT=ws_number
```

After this run `docker-compose up` in the directory containing the .yml

### "natively"

(Note that I built it with python 3.9, older versions should work too though.)
running it on your machine directly can be done too but needs some pip dependencies (websockets, mcrcon) first:
I recommend doing this in a venv btw.

`pip3 install -r requirements.txt`

After this you need to set the following env variables (those are mandatory, but there are a few others below):

`export RCON_HOST=mcserver_ip`
`export RCON_PASSWORD=mcrcon_password`
`export WS_PORT=ws_number`

Then it can be launched by just using `python3 main.py`

### additional env variables
next to the env variables mentioned above, there are also a few more:
  - `RCON_PORT` the RCON port. Defaults to 25575.
  - `REFRESH_RATE` The amount of WebSocket messages sent to clients per second. Defaults to 10. Lowering it reduces bandwidth usage but makes movements on the map choppier. Accordingly increasing it smoothes movements but increases bandwidth usage.

### nginx reverse proxying

Serving the WebSocket can be made simple by reverse-proxying it.
As opposed to exposing the WebSocket port directly, this is required when serving the Overviewer map via HTTPS, or just for the sake of it. 
For that, edit your default site (usually `/etc/nginx/sites-enabled/default`) and add a new route with the following content:
(note that the proxy_pass port needs to be changed to whatever you chose earlier)

```
location /mcplayerlocation {
  proxy_set_header HOST $host;
  proxy_set_header X-Real-IP $remote_addr;
  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  proxy_set_header X-Forwarded-Proto $scheme;
  proxy_pass_request_headers on;
  proxy_pass http://127.0.0.1:ws_port;
  proxy_http_version 1.1;
  proxy_set_header Upgrade $http_upgrade;
  proxy_set_header Connection "Upgrade";
}
```

Then reload nginx.

### integrating into Overviewer

Finally a few modifications to Overviewer need to be done.
you need to change into its directory. 
In there you'll find `overviewer_core/data/web_assets/index.html`.
Edit it and you'll find a bunch of `<script>` tags near the top. Add one more:

`<script type="text/javascript" src="client.js"></script>`

In case you're using HTTP instead of HTTPS for the Overviewer (or in general), you may wanna modify the `socketUrl:` line near the top in client.js and replace `wss://` with `ws:/`.

You may also wanna modify that line when using another setup than my nginx one above.

Unfortunately, Overviewer bundles its javascript and trying to put the client.js stuff in there breaks everything, so we need to serve it manually.
This can be done by chaining a cp behind the overviwer command, like so:

`python3 overviewer.py -c config && cp client.js /path/to/overviewer/out-dir/client.js`

(This assumes that client.js is put next to overviewer.py, otherwise point to its path)

### done

Now you're set! Enjoy live player locations :D

## TODOs

The whole thing ain't perfect yet. There are 3 things that need to be done in the client.js
  - Better error handling for nginx errors
    - most notably there is a HTTP 502 response issue that causes lots of loop cycles, bombing the RAM of people with the tab open when the server script isn't running (so make sure that mcpl.py is running when you serve the map or users are gonna have a really bad time)
    - also it should try to reconnect on HTTP 504 responses, otherwise the user has to reload the page for it to work again
  - Support for different nothdirections
    - if the map has different north directions than `upper-left`, player positions will be off cause the client assumes it facing always there
  - Bukkit/Spigot/PaperMC multiple worlds support
    - most notably the proper handling for overworld/nether/end
    - while there seems to be support for it, this refers to the "default all-in-one world package"
    
Also there is one issue I haven't yet wrapped my head around: **Support for Firefox/mobile browsers**
  - for some reason Firefox won't connect to the websocket. Chromium-based stuff does however.
  - on mobile the issue is probably the same, I didn't debug that one closer yet though.
