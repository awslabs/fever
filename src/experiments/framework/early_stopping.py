import torch
import os
class EarlyStopping():

    def __init__(self,name,model_name,model,patience):
        self.model = model
        self.path = os.path.join(os.getenv("MODEL_DIR", "models"), name, model_name)

        self.best_epoch = 0
        self.epoch_count = 0
        self.best_score = 0

        self.patience = patience

        if not os.path.exists(self.path):
            os.makedirs(self.path)

    def check(self,epoch,accuracy_history):
        self.epoch_count = max(epoch,self.epoch_count)

        torch.save(self.model.state_dict(), os.path.join(self.path, "epoch-" + str(epoch) + ".model"))

        if accuracy_history[-1]>=self.best_score:
            self.best_epoch = epoch
            self.best_score = accuracy_history[-1]

        if epoch > (self.best_epoch+self.patience):
            self.model.load_state_dict(torch.load(os.path.join(self.path, "epoch-" + str(self.best_epoch) + ".model")))
            raise StopIteration()

    def cleanup(self):
        self.model.load_state_dict(torch.load(os.path.join(self.path, "epoch-" + str(self.best_epoch) + ".model")))

        for i in range(self.epoch_count):
            try:
                os.unlink(os.path.join(self.path, "epoch-" + str(i) + ".model"))
            except FileNotFoundError:
                pass


        torch.save(self.model.state_dict(), os.path.join(self.path, "final.model"))

