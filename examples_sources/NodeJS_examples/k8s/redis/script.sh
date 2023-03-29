helm install redis bitnami/redis -n redis --create-namespace --set auth.enabled=fals

helm template redis bitnami/redis -n redis --create-namespace --set auth.enabled=false > redius-template.yaml
