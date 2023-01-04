FROM node:14.8.0-alpine3.12

WORKDIR .

COPY package.json ./
COPY package-lock.json ./

ENV PATH="${PATH}:/mnt/c/Windows/System32"

RUN npm install
RUN npm install react-scripts@3.4.0 -g

CMD ["pwd"]
COPY . ./

EXPOSE 3000

CMD ["npm", "start"]

