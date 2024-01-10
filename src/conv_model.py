import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import os
import requests
from torch import load

from game_objects.constant import MODEL_URL

class Conv_QNet(nn.Module):
    def __init__(self, input_channels, num_actions):
        super().__init__()
        self.conv1 = nn.Conv2d(input_channels, 32, kernel_size=8, stride=4)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=4, stride=2)
        self.conv3 = nn.Conv2d(64, 64, kernel_size=3, stride=1)

        # Compute size of the output from the last Conv layer
        self.conv_output_size = self._get_conv_output([input_channels, 84, 84])

        # Fully connected layers
        self.fc = nn.Linear(self.conv_output_size, 512)
        self.out = nn.Linear(512, num_actions)
        

    def _get_conv_output(self, shape):
        with torch.no_grad():
            return self.conv3(self.conv2(self.conv1(torch.zeros(1, *shape)))).view(1, -1).size(1)

    def forward(self, x):
        x = F.relu(self.conv1(x))
        x = F.relu(self.conv2(x))
        x = F.relu(self.conv3(x))
        x = x.view(x.size(0), -1)
        x = x.view(-1, self.conv_output_size)
        x = F.relu(self.fc(x))
        return self.out(x)
    
    def download_model_from_github(url, local_dir='./model', file_name='model.pth'):
        if not os.path.exists(local_dir):
            os.makedirs(local_dir)

        local_file_path = os.path.join(local_dir, file_name)
        response = requests.get(url)

        with open(local_file_path, 'wb') as file:
            file.write(response.content)
            
        print(f"Model downloaded and saved to {local_file_path}")


    def save(self, file_name='model.pth'):
        model_folder_path = './model'
        if not os.path.exists(model_folder_path):
            os.makedirs(model_folder_path)

        file_name = os.path.join(model_folder_path, file_name)
        torch.save(self.state_dict(), file_name)
    
    def load(self, file_name='model.pth'):
        try:
            self.download_model_from_github(MODEL_URL)
        except:
            print("Unable to download model from github. Check your internet connection")


        model_folder_path = './model'
        file_path = os.path.join(model_folder_path, file_name)
        if os.path.exists(file_path):
            self.load_state_dict(torch.load(file_path))
            print("Loaded saved model from", file_path)
        else:
            print("No saved model found at", file_path)


class Conv_QTrainer:
    def __init__(self, model, lr, gamma, device='cpu'):
        self.lr = lr
        self.gamma = gamma
        self.model = model.to(device)
        self.device = device
        self.optimizer = optim.Adam(model.parameters(), lr=self.lr)
        self.criterion = nn.MSELoss()

    def train_step(self, states, actions, rewards, next_states, dones):

        states = torch.tensor(states, dtype=torch.float).to(self.device)
        next_states = torch.tensor(next_states, dtype=torch.float).to(self.device)
        actions = torch.tensor(actions, dtype=torch.long).to(self.device)
        rewards = torch.tensor(rewards, dtype=torch.float).to(self.device)
        dones = torch.tensor(dones, dtype=torch.uint8).to(self.device)

        # 1: predicted Q values with current state
        pred = self.model(states)

        target = pred.clone()
        for idx in range(len(dones)):
            Q_new = rewards[idx]
            if not dones[idx]:
                Q_new = rewards[idx] + self.gamma * torch.max(self.model(next_states[idx]))

            target[idx][torch.argmax(actions[idx]).item()] = Q_new

        self.optimizer.zero_grad()
        loss = self.criterion(target, pred)
        loss.backward()

        self.optimizer.step()


