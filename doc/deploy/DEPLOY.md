# dictManager deployment on server 

# check for exissting image versions

```
docker images dictmanager --format 'table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.CreatedSince}}\t{{.Size}}'
``` 



# delete current container

```
 docker rm -f dictmanager 
```


# set ssh agent
```
eval "$(ssh-agent -s)"

# 2) Add your deploy key
ssh-add ~/.ssh/deploy-dictmanager

# 3) Confirm agent + key
echo "$SSH_AUTH_SOCK"
ssh -T git@github.com  # should say "Hi <user>!" or similar (it will fail at shell, that's OK)

# 4) Build, explicitly passing the socket
docker buildx build --no-cache --pull \
  --ssh default="$SSH_AUTH_SOCK" \
  -t dictmanager:$(date +%Y%m%d%H%M) \
  --build-arg REPO=git@github.com:jakob-beetz/dictBench.git \
  --build-arg BRANCH=main .
```
# Pull from git and build docker

```
docker buildx build --no-cache --pull --ssh default -t "$TAG"   --build-arg REPO=git@github.com:jakob-beetz/dictBench.git   --build-arg BRANCH=main .
```

# run (make sure the date stamp of dictmanager: is set to latest)

```
docker run -d --name dictmanager -p 8080:8000   -v dj_appdata:/app/propbench   -e DJANGO_ALLOWED_HOSTS="dictmanager.semantic-collab.eu,localhost,127.0.0.1"   -e DJANGO_SECRET_KEY="change-me"   -e CSRF_TRUSTED_ORIGINS="https://dictmanager.semantic-collab.eu"   dictmanager:202508311636   gunicorn --chdir /app/propbench -b 0.0.0.0:8000 propbench.wsgi:application 
```


# inspect database in docker volume

```
 docker run --rm -it -v dj_appdata:/data alpine sh -c   "apk add --no-cache sqlite && sqlite3 data/db.sqlite3"
