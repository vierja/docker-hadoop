ssh-keygen -f master -t rsa -N ''
ssh hduser@10.0.10.1 -i keys/master -o StrictHostKeyChecking=no -q
hola