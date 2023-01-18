# -*- coding: utf-8 -*-
"""MultiGPU-AET.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1wNR4ISt1KaF-ctJlHt6K0Jw_IG9AvMCe
"""

import torch
import torch.nn as nn
from sklearn.cluster import KMeans
from torch.utils.data import Subset
import numpy as np


class AutoEncoder(nn.Module):
    def __init__(self):
        super(AutoEncoder, self).__init__()

        # Encoder layers
        self.conv1 = nn.Conv2d(in_channels=3, out_channels=32, kernel_size=3, stride=1, padding=1)
        self.conv2 = nn.Conv2d(in_channels=32, out_channels=64, kernel_size=3, stride=1, padding=1)
        self.conv3 = nn.Conv2d(in_channels=64, out_channels=128, kernel_size=3, stride=1, padding=1)

        # Decoder layers
        self.deconv1 = nn.ConvTranspose2d(in_channels=128, out_channels=64, kernel_size=3, stride=1, padding=1)
        self.deconv2 = nn.ConvTranspose2d(in_channels=64, out_channels=32, kernel_size=3, stride=1, padding=1)
        self.deconv3 = nn.ConvTranspose2d(in_channels=32, out_channels=3, kernel_size=3, stride=1, padding=1)

    def forward(self, x):
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.conv3(x)

        x = self.deconv1(x)
        x = self.deconv2(x)
        x = self.deconv3(x)

        return x


    def encoder(self, x):
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.conv3(x)
        return x

import torch
from torchvision import datasets, transforms

# Define the transform to normalize the data
transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
])

# Load the CIFAR-10 dataset
cifar10_train = datasets.CIFAR10(root='path/to/data', train=True, download=True, transform=transform)
cifar10_test = datasets.CIFAR10(root='path/to/data', train=False, download=True, transform=transform)

# Define the indices of the images to use
indices = list(range(600))
# Create the subset of the dataset
subset_train = Subset(cifar10_train, indices)
subset_test = Subset(cifar10_test, indices)

# Create the DataLoader
train_loader = torch.utils.data.DataLoader(subset_train, batch_size=64, shuffle=True)
test_loader = torch.utils.data.DataLoader(subset_test, batch_size=64, shuffle=True)

# Initialize the model and move it to the GPU
model = AutoEncoder()
if torch.cuda.is_available():
    model = model.cuda()

# Define the criterion and optimizer
criterion = nn.MSELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
num_epochs=2
print("Training Started...")
# Training loop
for epoch in range(num_epochs):
    train_loss = 0.0
    train_acc = 0.0
    for data, _ in train_loader:
        # Move the data to the GPU
        if torch.cuda.is_available():
            data = data.cuda()

        optimizer.zero_grad()
        output = model(data)
        loss = criterion(output, data)
        loss.backward()
        optimizer.step()

        # Accumulate the training loss and accuracy
        train_loss += loss.item()
        train_acc += (output == data).sum().item() / len(data)

    # Print the epoch, loss, and accuracy
    train_loss /= len(train_loader)
    train_acc /= len(train_loader)
    print(f'Epoch {epoch+1} - Loss: {train_loss:.4f} - Accuracy: {train_acc:.4f}')

# Import the necessary libraries
from sklearn.cluster import KMeans

# Number of clusters for the codebook
num_clusters = 100

# Create an empty list to store the encoded data
encoded_data = []

# Create an empty list to store the labels
labels = []

# Loop through the train and test data
for data, label in train_loader:
    # Move the data to the GPU
    if torch.cuda.is_available():
        data = data.cuda()
    # Pass the data through the encoder
    encoded = model.encoder(data)
    # Reshape the encoded data to 1D
    encoded = encoded.view(encoded.size(0), -1)
    # Add the encoded data to the list
    encoded_data.append(encoded.cpu().detach().numpy())
    # Add the labels to the list
    labels.append(label.numpy())

# Concatenate the encoded data and labels from the train and test set
encoded_data = np.concatenate(encoded_data, axis=0)
labels = np.concatenate(labels, axis=0)

# Create a dictionary to map the labels to the encoded data
data_labels = {'encoded_data': encoded_data, 'labels': labels}

# Train the codebook using k-means clustering
kmeans = KMeans(n_clusters=num_clusters, random_state=0)
kmeans.fit(data_labels['encoded_data'])

# Get the cluster centers
codebook = kmeans.cluster_centers_

# Import the necessary libraries
import torch
from torch.nn import Transformer

# Define the number of classes
num_classes = 10

# Create a mapping from the labels to the codebook
label_codebook = {label: codebook[i] for i, label in enumerate(np.unique(labels))}

# Create a new list to store the codebook values for each data point
codebook_data = [label_codebook[label] for label in labels]

# Convert the codebook data to a tensor
#codebook_data = torch.tensor(codebook_data)

# Convert the labels to a tensor
#labels = torch.tensor(labels)

# Convert the codebook data to a LongTensor
codebook_data = torch.LongTensor(codebook_data)

# Convert the labels to a LongTensor
labels = torch.LongTensor(labels)

class AutoregressiveTransformer(nn.Module):
    def __init__(self, num_classes, codebook_size, d_model, nhead):
        super(AutoregressiveTransformer, self).__init__()
        self.embedding = nn.Embedding(codebook_size, d_model)
        self.transformer = nn.Transformer(d_model, nhead)
        self.fc = nn.Linear(d_model, num_classes)

    def forward(self, x,  tgt):
        x = self.embedding(x)
        x = self.transformer(x)
        x = self.fc(x)
        return x

# Number of classes
num_classes = 10
# Codebook size
codebook_size = num_clusters
# Model dimension
d_model = 256
# Number of heads in multi-head attention
nhead = 4


# Initialize the model
model = AutoregressiveTransformer(num_classes, codebook_size, d_model, nhead)

# Move the model to multiple GPUs
if torch.cuda.device_count() > 1:
    model = nn.DataParallel(model)

if torch.cuda.is_available():
    model = model.cuda()

# Define the optimizer
optimizer = torch.optim.Adam(model.parameters())
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)


# Define the criterion
criterion = nn.CrossEntropyLoss()

# Training loop
num_epochs = 5
# Training loop
for epoch in range(num_epochs):
    train_loss = 0.0
    train_acc = 0.0
    for data, label in zip(codebook_data, labels):
        # Move the data and label to the GPU
        if torch.cuda.is_available():
            data = data.cuda()
            label = label.cuda()
            codebook_data = codebook_data.cuda()

        # Zero the gradients
        optimizer.zero_grad()

        # Forward pass
        output = model(codebook_data,label)

        # Compute the loss
        loss = criterion(output, label)

        # Backward pass and optimization
        loss.backward()
        optimizer.step()

        # Accumulate the training loss and accuracy
        train_loss += loss.item()
        train_acc += (output.argmax(1) == label).float().mean

    # Print the training loss and accuracy for each epoch
    print(f'Epoch {epoch+1}, Loss: {train_loss/len(train_loader)}, Accuracy: {train_acc/len(train_loader)}')

