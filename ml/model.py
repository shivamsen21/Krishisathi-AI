import torch
import torch.nn as nn
from torchvision.models import mobilenet_v2, MobileNet_V2_Weights


class MobileNetV2CropDisease(nn.Module):
    def __init__(self, num_classes: int, pretrained: bool = True, freeze_backbone: bool = True):
        super().__init__()
        self.num_classes = num_classes

        weights = MobileNet_V2_Weights.IMAGENET1K_V1 if pretrained else None
        self.backbone = mobilenet_v2(weights=weights)

        in_features = self.backbone.classifier[1].in_features
        self.backbone.classifier = nn.Sequential(
            nn.Dropout(p=0.2, inplace=False),
            nn.Linear(in_features, num_classes),
        )

        if freeze_backbone:
            self.freeze_backbone()

    def freeze_backbone(self) -> None:
        for param in self.backbone.features.parameters():
            param.requires_grad = False

    def unfreeze_backbone(self, num_layers: int = 7) -> None:
        features = list(self.backbone.features.children())
        for layer in features[-num_layers:]:
            for param in layer.parameters():
                param.requires_grad = True

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.backbone(x)

    def get_backbone_params(self):
        return self.backbone.features.parameters()

    def get_classifier_params(self):
        return self.backbone.classifier.parameters()


def create_model(
    num_classes: int,
    pretrained: bool = True,
    freeze_backbone: bool = True,
    device: torch.device = torch.device("cpu"),
) -> MobileNetV2CropDisease:
    model = MobileNetV2CropDisease(
        num_classes=num_classes,
        pretrained=pretrained,
        freeze_backbone=freeze_backbone,
    )
    return model.to(device)