package data

import (
	"context"
	"github.com/redis/go-redis/v9"
)

// Redis a struct for exposing redis client for save/load operation
type Redis struct {
	redisClient *redis.Client
	ctx         context.Context
}

// NewRedis return a new redis client
func NewRedis(address string) Redis {
	client := redis.NewClient(&redis.Options{
		Addr: address,
	})

	return Redis{
		redisClient: client,
		ctx:         context.Background(),
	}
}

// Set save a new key/value pair into redis
func (r Redis) Set(key, val string) error {
	return r.redisClient.Set(r.ctx, key, val, 0).Err()
}

// Get return the value in string given a redis key
func (r Redis) Get(key string) (string, error) {
	return r.redisClient.Get(r.ctx, key).Result()
}

// CloseConnection terminate the connection to redis
func (r Redis) CloseConnection() error {
	return r.redisClient.Close()
}
