#pragma once

#include "AI4AnimationNNETypes.generated.h"

USTRUCT(BlueprintType)
struct AI4ANIMATIONNNE_API FAI4AnimationNNEModelIOInfo
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "AI4Animation|NNE")
	FString InputName;

	UPROPERTY(BlueprintReadOnly, Category = "AI4Animation|NNE")
	FString OutputName;

	UPROPERTY(BlueprintReadOnly, Category = "AI4Animation|NNE")
	TArray<int32> InputShape;

	UPROPERTY(BlueprintReadOnly, Category = "AI4Animation|NNE")
	int32 OpsetVersion = 17;

	UPROPERTY(BlueprintReadOnly, Category = "AI4Animation|NNE")
	bool bDynamicBatch = true;
};

USTRUCT(BlueprintType)
struct AI4ANIMATIONNNE_API FAI4AnimationNNERetargetingInfo
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "AI4Animation|NNE")
	FString PrimaryUESkeleton;

	UPROPERTY(BlueprintReadOnly, Category = "AI4Animation|NNE")
	bool bSupportsCustomSkeletons = true;

	UPROPERTY(BlueprintReadOnly, Category = "AI4Animation|NNE")
	FString Strategy;
};

USTRUCT(BlueprintType)
struct AI4ANIMATIONNNE_API FAI4AnimationNNETerrainInfo
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "AI4Animation|NNE")
	bool bSupportsVariableSlope = true;

	UPROPERTY(BlueprintReadOnly, Category = "AI4Animation|NNE")
	bool bSupportsHeightVariation = true;

	UPROPERTY(BlueprintReadOnly, Category = "AI4Animation|NNE")
	FString TrainingExpectation;
};

USTRUCT(BlueprintType)
struct AI4ANIMATIONNNE_API FAI4AnimationNNEModelPackage
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "AI4Animation|NNE")
	FString SchemaVersion;

	UPROPERTY(BlueprintReadOnly, Category = "AI4Animation|NNE")
	FString PackageName;

	UPROPERTY(BlueprintReadOnly, Category = "AI4Animation|NNE")
	FString RuntimeName;

	UPROPERTY(BlueprintReadOnly, Category = "AI4Animation|NNE")
	FString ManifestPath;

	UPROPERTY(BlueprintReadOnly, Category = "AI4Animation|NNE")
	FString OnnxPath;

	UPROPERTY(BlueprintReadOnly, Category = "AI4Animation|NNE")
	FString SourceCheckpoint;

	UPROPERTY(BlueprintReadOnly, Category = "AI4Animation|NNE")
	int32 SampleRate = 30;

	UPROPERTY(BlueprintReadOnly, Category = "AI4Animation|NNE")
	TArray<FString> BoneNames;

	UPROPERTY(BlueprintReadOnly, Category = "AI4Animation|NNE")
	TArray<FString> CompatibleInputFormats;

	UPROPERTY(BlueprintReadOnly, Category = "AI4Animation|NNE")
	FAI4AnimationNNEModelIOInfo ModelIO;

	UPROPERTY(BlueprintReadOnly, Category = "AI4Animation|NNE")
	FAI4AnimationNNERetargetingInfo Retargeting;

	UPROPERTY(BlueprintReadOnly, Category = "AI4Animation|NNE")
	FAI4AnimationNNETerrainInfo Terrain;

	UPROPERTY(BlueprintReadOnly, Category = "AI4Animation|NNE")
	TMap<FString, FString> ExtraMetadata;

	bool IsValid() const
	{
		return !PackageName.IsEmpty() && !OnnxPath.IsEmpty();
	}
};
