# syntax=docker/dockerfile:1

FROM node:18.7.0

run apt-get -y update && apt-get install -y git-core

WORKDIR /app

COPY ["package.json", "package-lock.json*", "./"]
COPY libm.so.6 /lib/x86_64-linux-gnu/

RUN npm install --production
RUN npm install pm2 -g

COPY . .

EXPOSE 8080

# CMD [ "node", "paceval-server.js" ]
CMD ["pm2-runtime", "paceval-server.js", "--expose-gc --max-old-space-size=6144"]
