package controllers

import (
	"context"
	"github.com/redis/go-redis/v9"
)

type Redis struct {
	redisClient *redis.Client
	ctx         context.Context
}

func NewRedis(address string) Redis {
	client := redis.NewClient(&redis.Options{
		Addr: address,
	})

	return Redis{
		redisClient: client,
		ctx:         context.Background(),
	}
}

func (r Redis) Get(key string) (string, error) {
	return r.redisClient.Get(r.ctx, key).Result()
}

func (r Redis) Exist(key string) bool {
	exist := r.redisClient.Exists(r.ctx, key).Val()

	if exist == 1 {
		return true
	}

	return false
}

func (r Redis) Delete(key string) error {
	return r.redisClient.Del(r.ctx, key).Err()
}

func (r Redis) CloseConnection() error {
	return r.redisClient.Close()
}
