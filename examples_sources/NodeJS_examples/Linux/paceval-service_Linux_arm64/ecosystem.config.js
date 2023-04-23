module.exports = {
  apps : [{
    name   : "paceval-service",
    script : "/home/paceval/sambashare/paceval-service_Linux_arm32/paceval-server.js"
    env_production: {
       NODE_ENV: "production",
       "PORT": "8080"
    }
  }]
}
