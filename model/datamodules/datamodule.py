import functools
from typing import Optional

from torch.utils.data import DataLoader

from pytorch_lightning import LightningDataModule
from model.datamodules.dataset import Dataset


class Datamodule(LightningDataModule):
    def __init__(self, _config):
        super().__init__()

        self.data_dir = _config["data_root"]

        self.num_workers = _config["num_workers"]
        self.batch_size = _config["per_gpu_batchsize"]
        self.eval_batch_size = self.batch_size

        self.draw_false_grid = _config["draw_false_grid"]
        self.img_size = _config["img_size"]

    @property
    def dataset_cls(self):
        return Dataset

    def set_train_dataset(self):
        self.train_dataset = self.dataset_cls(
            self.data_dir,
            split="train",
            draw_false_grid=self.draw_false_grid,
        )

    def set_val_dataset(self):
        self.val_dataset = self.dataset_cls(
            self.data_dir,
            split="val",
            draw_false_grid=self.draw_false_grid,
        )

    def set_test_dataset(self):
        self.test_dataset = self.dataset_cls(
            self.data_dir,
            split="test",
            draw_false_grid=self.draw_false_grid,
        )

    def setup(self, stage: Optional[str] = None):
        if stage in (None, "fit"):
            self.set_train_dataset()
            self.set_val_dataset()

        if stage in (None, "test"):
            self.set_test_dataset()

        self.collate = functools.partial(
            self.train_dataset.collate,
            img_size=self.img_size,
        )

    def train_dataloader(self) -> DataLoader:
        return DataLoader(
            self.train_dataset,
            batch_size=self.batch_size,
            num_workers=self.num_workers,
            collate_fn=self.collate,
        )

    def val_dataloader(self) -> DataLoader:
        return DataLoader(
            self.val_dataset,
            batch_size=self.batch_size,
            num_workers=self.num_workers,
            collate_fn=self.collate,
        )

    def test_dataloader(self) -> DataLoader:
        return DataLoader(
            self.test_dataset,
            batch_size=self.batch_size,
            num_workers=self.num_workers,
            collate_fn=self.collate,
        )