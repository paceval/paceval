FROM golang:1.19 AS backendBuilder

WORKDIR /go/src/github.com/catena-x/gh-org-checks

COPY . .

RUN CGO_ENABLED=0 GOOS=linux go build -o /go/bin/main main.go

#use a small image to run
FROM alpine:3.16 as runner

RUN apk update && apk upgrade
RUN apk add --no-cache tzdata

WORKDIR /home/appuser

COPY --from=backendBuilder /go/bin/main .

EXPOSE 8080
ENTRYPOINT ["./main"]
