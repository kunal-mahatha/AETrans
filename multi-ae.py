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
indices = list(range(50000))
# Create the subset of the dataset
subset_train = Subset(cifar10_train, indices)
subset_test = Subset(cifar10_test, indices)

# Create the DataLoader
train_loader = torch.utils.data.DataLoader(subset_train, batch_size=64, shuffle=True)
test_loader = torch.utils.data.DataLoader(subset_test, batch_size=64, shuffle=True)

# Initialize the model and move it to the GPU
model = AutoEncoder()

# Move the model to multiple GPUs
if torch.cuda.device_count() > 1:
    model = nn.DataParallel(model)

if torch.cuda.is_available():
    model = model.cuda()

# Define the criterion and optimizer
criterion = nn.MSELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
num_epochs=200
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
