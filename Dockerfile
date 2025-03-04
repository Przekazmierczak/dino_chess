# Use the official Python runtime image
FROM python:3.11.3-slim
 
# Create the app directory
RUN mkdir /app
 
# Set the working directory inside the container
WORKDIR /app
 
# Prevents Python from writing pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1
#Prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1 
 
# Upgrade pip
RUN pip install --upgrade pip 
 
# Copy the Django project  and install dependencies
COPY requirements.txt  /app/
 
# Run this command to install all dependencies 
RUN pip install --no-cache-dir -r requirements.txt
 
# Copy the Django project to the container
COPY . /app/

# Create a new user
RUN adduser --disabled-password --gecos "" djangouser

# Set the correct ownership and permissions for the database
RUN chown -R djangouser:djangouser /app/chess_django

# Set the user to djangouser
USER djangouser
 
# Expose the Django port
EXPOSE 8000
 
# Run Django’s development server
CMD ["python", "chess_django/manage.py", "runserver", "0.0.0.0:8000"]