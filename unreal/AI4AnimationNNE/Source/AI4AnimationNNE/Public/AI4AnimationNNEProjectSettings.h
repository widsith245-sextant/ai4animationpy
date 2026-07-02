#pragma once

#include "Engine/DeveloperSettings.h"

#include "AI4AnimationNNEProjectSettings.generated.h"

UCLASS(Config = Game, DefaultConfig, meta = (DisplayName = "AI4Animation NNE"))
class AI4ANIMATIONNNE_API UAI4AnimationNNEProjectSettings : public UDeveloperSettings
{
	GENERATED_BODY()

public:
	UAI4AnimationNNEProjectSettings();

	virtual FName GetCategoryName() const override;

	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Packages")
	bool bPreferPluginResourceDirectory = true;

	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Packages")
	FString RelativeModelPackageRoot = TEXT("Resources/ModelPackages");

	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Packages")
	FString DefaultPackageName;

	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Runtime")
	FString DefaultRuntimeName = TEXT("NNERuntimeORTCpu");

	UPROPERTY(Config, EditAnywhere, BlueprintReadOnly, Category = "Runtime")
	bool bLoadDefaultPackageOnInitialize = false;
};
