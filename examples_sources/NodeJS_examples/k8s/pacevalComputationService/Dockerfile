# syntax=docker/dockerfile:1

FROM node:18.7.0

RUN apt-get -y update && apt-get install -y git-core

WORKDIR /app

COPY ["package.json", "package-lock.json*", "./"]

RUN npm install --production
RUN npm install pm2 -g

COPY . .

EXPOSE 8080

# CMD [ "node", "paceval-server.js" ]
CMD ["pm2-runtime", "paceval-server.js", "--node-args=\"--expose-gc\"","--max-old-space-size=6144"]
