# syntax=docker/dockerfile:1

FROM arm64v8/node:16

WORKDIR /app

COPY ["package.json", "package-lock.json*", "./"]

RUN npm install

COPY . .

EXPOSE 8080

CMD [ "node", "paceval-server.js" ] 
