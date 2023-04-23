helm install redis bitnami/redis -n redis --create-namespace --set auth.enabled=false

helm template redis bitnami/redis -n redis --create-namespace --set auth.enabled=false > redis-template.yaml
