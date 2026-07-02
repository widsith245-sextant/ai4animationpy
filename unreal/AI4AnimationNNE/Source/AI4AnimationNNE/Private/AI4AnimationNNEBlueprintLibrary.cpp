#include "AI4AnimationNNEBlueprintLibrary.h"

#include "AI4AnimationNNESubsystem.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"

UAI4AnimationNNESubsystem* UAI4AnimationNNEBlueprintLibrary::GetAI4AnimationNNESubsystem(const UObject* WorldContextObject)
{
	if (WorldContextObject == nullptr || GEngine == nullptr)
	{
		return nullptr;
	}

	if (const UWorld* World = GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::ReturnNull))
	{
		if (UGameInstance* GameInstance = World->GetGameInstance())
		{
			return GameInstance->GetSubsystem<UAI4AnimationNNESubsystem>();
		}
	}

	return nullptr;
}
