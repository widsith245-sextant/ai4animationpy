#pragma once

#include "Subsystems/GameInstanceSubsystem.h"
#include "Templates/SharedPointer.h"

#include "AI4AnimationNNETypes.h"

#include "AI4AnimationNNESubsystem.generated.h"

class UNNEModelData;

namespace UE::NNE
{
	class IModelCPU;
	class IModelInstanceCPU;
}

UCLASS(BlueprintType)
class AI4ANIMATIONNNE_API UAI4AnimationNNESubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	UFUNCTION(BlueprintCallable, Category = "AI4Animation|NNE")
	bool LoadDefaultPackage();

	UFUNCTION(BlueprintCallable, Category = "AI4Animation|NNE")
	bool LoadPackageByName(const FString& PackageName);

	UFUNCTION(BlueprintCallable, Category = "AI4Animation|NNE")
	bool LoadPackageFromManifest(const FString& ManifestPath);

	UFUNCTION(BlueprintCallable, Category = "AI4Animation|NNE")
	bool RunInference(const TArray<float>& Input, TArray<float>& Output);

	UFUNCTION(BlueprintPure, Category = "AI4Animation|NNE")
	bool IsModelLoaded() const;

	UFUNCTION(BlueprintPure, Category = "AI4Animation|NNE")
	const FAI4AnimationNNEModelPackage& GetActivePackage() const;

	UFUNCTION(BlueprintPure, Category = "AI4Animation|NNE")
	FString GetLastError() const;

	UFUNCTION(BlueprintPure, Category = "AI4Animation|NNE")
	int32 GetExpectedInputElementCount() const;

private:
	bool ParseManifest(const FString& ManifestPath, FAI4AnimationNNEModelPackage& OutManifest, FString& OutError) const;
	bool CreateModelInstanceFromPackage(const FAI4AnimationNNEModelPackage& InPackage, FString& OutError);
	FString ResolveModelPackageRoot() const;
	void ResetRuntimeState();

private:
	UPROPERTY(Transient)
	TObjectPtr<UNNEModelData> RuntimeModelData;

	FAI4AnimationNNEModelPackage ActivePackage;
	FString LastError;
	TSharedPtr<UE::NNE::IModelCPU> Model;
	TSharedPtr<UE::NNE::IModelInstanceCPU> ModelInstance;
};
