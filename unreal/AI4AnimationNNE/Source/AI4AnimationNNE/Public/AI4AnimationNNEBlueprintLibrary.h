#pragma once

#include "Kismet/BlueprintFunctionLibrary.h"

#include "AI4AnimationNNEBlueprintLibrary.generated.h"

class UAI4AnimationNNESubsystem;

UCLASS()
class AI4ANIMATIONNNE_API UAI4AnimationNNEBlueprintLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintPure, Category = "AI4Animation|NNE", meta = (WorldContext = "WorldContextObject"))
	static UAI4AnimationNNESubsystem* GetAI4AnimationNNESubsystem(const UObject* WorldContextObject);
};
