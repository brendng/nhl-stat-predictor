import torch
import torch.nn as nn

class HockeyLSTM(nn.Module):
    def __init__(self, input_dim, output_dim, hidden_dim=64, num_layers=2, dropout=0.2):
        super(HockeyLSTM, self).__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim,
                            num_layers=num_layers,
                            batch_first=True,
                            dropout=dropout)
        self.fc = nn.Linear(hidden_dim, output_dim)

    def forward(self, x):
        _, (hn, _) = self.lstm(x)
        out = hn[-1]
        return self.fc(out)
