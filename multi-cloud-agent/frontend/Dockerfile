# Use Node.js base image
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy only package.json and package-lock.json to install dependencies first
COPY package*.json ./

# Install dependencies
RUN npm install

# Now copy the rest of the app
COPY . .

# Expose port (if running React dev server inside container)
EXPOSE 3000

# Start the development server
CMD ["npm", "start"]
