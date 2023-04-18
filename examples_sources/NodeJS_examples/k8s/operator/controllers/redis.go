package controllers

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

// Get return the value in string given a redis key
func (r Redis) Get(key string) (string, error) {
	return r.redisClient.Get(r.ctx, key).Result()
}

// Exist return a boolean if the given key exist in redis
func (r Redis) Exist(key string) bool {
	exist := r.redisClient.Exists(r.ctx, key).Val()

	if exist == 1 {
		return true
	}

	return false
}

// Delete delete a key in redis
func (r Redis) Delete(key string) error {
	return r.redisClient.Del(r.ctx, key).Err()
}

// CloseConnection terminate the connection to redis
func (r Redis) CloseConnection() error {
	return r.redisClient.Close()
}
