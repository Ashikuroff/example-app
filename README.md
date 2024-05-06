# we have local kind k8s cluster
1. created local kind k8s cluster (One control plane,2 worker node)
2. Deployed ArgoCD gitops tools for application deployment in k8s
3. create CI/CD pipeline to build docker image and push to docker hub
4. created sample example-app and deployed it to k8s cluster via ArgoCD
5. Since Gitops tools ArgoCD is pull model tools if any changes on code on github on deployment or anyother files, argocd will sync
   automatically and re-deploy in k8s cluster

6. All details and code can be found here
     https://github.com/Ashikuroff/example-app
