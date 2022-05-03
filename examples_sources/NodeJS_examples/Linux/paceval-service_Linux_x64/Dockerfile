# syntax=docker/dockerfile:1

FROM node:16

WORKDIR /app

COPY ["package.json", "package-lock.json*", "./"]
COPY libm.so.6 /lib/x86_64-linux-gnu/

RUN npm install

COPY . .

EXPOSE 8080

CMD [ "node", "paceval-server.js" ] 
