# Install using Helm

## Add helm repo

`helm repo add grafana https://grafana.github.io/helm-charts`

## Update helm repo

`helm repo update`

## Install helm 

`helm install grafana grafana/grafana`

## Expose Grafana Service

`kubectl expose service grafana — type=NodePort — target-port=3000 — name=grafana-ext`
 'kubectl --namespace default port-forward grafana-67fb78c5bf-f5dkl 3000'

# how to get admin password for grafana

kubectl get secret --namespace default grafana -o jsonpath="{.data.admin-password}" | base64 --decode ; echo

# add promethues as data source

URL filed add <promethues-server:ip:80>
<http://10.96.40.128:80>

# import k8s default metric in dashboard

ID - 6417
