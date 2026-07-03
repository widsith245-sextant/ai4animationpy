#pragma once

#include "Kismet/BlueprintFunctionLibrary.h"

#include "AI4AnimationNNEEditorLibrary.generated.h"

UCLASS()
class AI4ANIMATIONNNEEDITOR_API UAI4AnimationNNEEditorLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category = "AI4Animation|Editor")
	static bool ImportClipFromJson(
		const FString& JsonPath,
		const FString& DestinationPackagePath,
		const FString& AssetName,
		const FString& SkeletonAssetPath,
		const FString& PreviewMeshAssetPath,
		FString& OutAssetPath,
		FString& OutErrorMessage);

	UFUNCTION(BlueprintCallable, Category = "AI4Animation|Editor")
	static bool ImportMannyClipFromJson(
		const FString& JsonPath,
		const FString& DestinationPackagePath,
		const FString& AssetName,
		const FString& SkeletonAssetPath,
		const FString& PreviewMeshAssetPath,
		FString& OutAssetPath,
		FString& OutErrorMessage);
};
