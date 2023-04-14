package data

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

func (r Redis) Set(key, val string) error {
	return r.redisClient.Set(r.ctx, key, val, 0).Err()
}

func (r Redis) CloseConnection() error {
	return r.redisClient.Close()
}
