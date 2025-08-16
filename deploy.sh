#!/bin/bash
# deploy.sh - Deploy CHIMERA to Render

echo "🚀 Deploying CHIMERA Collective to Render..."

# Create deployment directory
mkdir -p chimera-collective-deploy
cd chimera-collective-deploy

# Copy necessary files
cp -r ../chimera ./
cp ../app.py ./
cp ../requirements.txt ./
cp ../render.yaml ./

# Initialize git
git init
git add .
git commit -m "Deploy CHIMERA Collective $(date +%Y%m%d-%H%M%S)"

# Push to Render
git remote add render https://github.com/YOUR_GITHUB/chimera-collective.git
git push render main

echo "✅ Deployment complete!"
echo "🌐 Your collective will be available at: https://chimera-collective.onrender.com"
