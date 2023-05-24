/*
Copyright 2023.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

package v1alpha1

import (
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// EDIT THIS FILE!  THIS IS SCAFFOLDING FOR YOU TO OWN!
// NOTE: json tags are required.  Any new fields you add must have json tags for the fields to be serialized.

// PacevalComputationObjectSpec defines the desired state of PacevalComputationObject
type PacevalComputationObjectSpec struct {
	// INSERT ADDITIONAL SPEC FIELDS - desired state of cluster
	// Important: Run "make" to regenerate code after modifying this file

	// FunctionID uniquely identifies an function
	// +kubebuilder:validation:Required:
	FunctionId string `json:"functionId,omitempty"`

	// +kubebuilder:validation:Required
	FunctionStr string `json:"functionStr,omitempty"`

	// +kubebuilder:default:="empty"
	Vars string `json:"Vars,omitempty"`

	// +kubebuilder:validation:Required
	NumOfVars string `json:"NumOfVars,omitempty"`

	// +kubebuilder:validation:Required
	Interval string `json:"Internal,omitempty"`
}

// PacevalComputationObjectStatus defines the observed state of PacevalComputationObject
type PacevalComputationObjectStatus struct {
	// INSERT ADDITIONAL STATUS FIELD - define observed state of cluster
	// Important: Run "make" to regenerate code after modifying this file

	// +optional
	// Endpoint Indicates the service DNS endpoint to call the function
	Endpoint string `json:"endpoint,omitempty" protobuf:"bytes,1,opt,name=endpoint"`

	// +optional
	// Ready Indicates whether custom resource object is ready for usage.
	//+kubebuilder:default:="False"
	Ready metav1.ConditionStatus `json:"ready,omitempty" protobuf:"bytes,2,opt,name=ready"`

	// +optional
	// LastActiveTime Indicates the timestamp where the object was active the last time.
	LastActiveTime metav1.Time `json:"lastActiveTime,omitempty" protobuf:"bytes,3,opt,name=lastActiveTime"`
}

//+kubebuilder:object:root=true
//+kubebuilder:subresource:status
//+kubebuilder:printcolumn:name="Ready",type=string,JSONPath=`.status.ready`
//+kubebuilder:printcolumn:name="Endpoint",type=string,JSONPath=`.status.endpoint`
//+kubebuilder:printcolumn:name="LastActiveTime",type=string,JSONPath=`.status.lastActiveTime`

// PacevalComputationObject is the Schema for the pacevalcomputationobjects API
type PacevalComputationObject struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec   PacevalComputationObjectSpec   `json:"spec,omitempty"`
	Status PacevalComputationObjectStatus `json:"status,omitempty"`
}

//+kubebuilder:object:root=true

// PacevalComputationObjectList contains a list of PacevalComputationObject
type PacevalComputationObjectList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`
	Items           []PacevalComputationObject `json:"items"`
}

func init() {
	SchemeBuilder.Register(&PacevalComputationObject{}, &PacevalComputationObjectList{})
}
