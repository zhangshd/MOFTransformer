import copy
import os
import pytorch_lightning as pl

from model.config import ex

from model.datamodules.datamodule import Datamodule
from model.modules.module import Module

from pytorch_lightning.plugins import DDPPlugin

import warnings

warnings.filterwarnings(
    "ignore", ".*Trying to infer the `batch_size` from an ambiguous collection.*"
)

@ex.automain
def main(_config):
    _config = copy.deepcopy(_config)
    pl.seed_everything(_config["seed"])

    dm = Datamodule(_config)
    model = Module(_config)
    exp_name = f"{_config['exp_name']}"

    os.makedirs(_config["log_dir"], exist_ok=True)
    checkpoint_callback = pl.callbacks.ModelCheckpoint(
        save_top_k=1,
        verbose=True,
        monitor="val/the_metric",
        mode="max",
        save_last=True,
    )

    logger = pl.loggers.TensorBoardLogger(
        _config["log_dir"],
        name=f'{exp_name}_seed{_config["seed"]}_from_{_config["load_path"].split("/")[-1][:-5]}',
    )

    lr_callback = pl.callbacks.LearningRateMonitor(logging_interval="step")
    callbacks = [checkpoint_callback, lr_callback]

    # gradient accumulation
    accumulate_grad_batches = _config["batch_size"] // (
        _config["per_gpu_batchsize"] * _config["num_gpus"] * _config["num_nodes"]
    )

    max_steps = _config["max_steps"] if _config["max_steps"] is not None else None

    trainer = pl.Trainer(
        gpus=_config["num_gpus"],
        num_nodes=_config["num_nodes"],
        precision=_config["precision"],
        strategy=DDPPlugin(find_unused_parameters=False),
        # deterministic=True,
        benchmark=True,
        max_epochs=_config["max_epoch"] if max_steps is None else 100,
        max_steps=max_steps,
        callbacks=callbacks,
        logger=logger,
        accumulate_grad_batches=accumulate_grad_batches,
        log_every_n_steps=10,
        resume_from_checkpoint=_config["resume_from"],
        val_check_interval=_config["val_check_interval"],
    )

    if not _config["test_only"]:
        trainer.fit(model, datamodule=dm)
    else:
        trainer.test(model, datamodule=dm)
