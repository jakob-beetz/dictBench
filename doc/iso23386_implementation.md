# ISO 23386:2020 Implementation in PropBench

This document outlines how the PropBench system implements the ISO 23386:2020 standard for building information modeling and other construction works.

## Overview of ISO 23386:2020

ISO 23386:2020 establishes the rules for defining properties in interconnected data dictionaries. It specifies:

- How to describe properties consistently with attributes
- How properties should be managed through a workflow process
- Rules for property validation, maintenance, and versioning

## Core Concepts Implemented

### 1. Property Structure

Each property in PropBench is structured according to ISO 23386, including:

- **Property Name**: Multilingual naming with contexts
- **Property Definition**: Clear description of the property's meaning
- **Value Format**: Data type and unit information
- **Physical Quantity**: Base quantities and derived quantities 
- **Validity Dates**: Time period when the property is valid
- **Status**: Current state in the workflow (draft, candidate, active, etc.)

### 2. Property Dictionary Management

PropBench implements dictionary management with:

- Version control for each property and dictionary
- Property grouping and hierarchical organization
- Import/export functionality for property exchange
- Validation rules for property attributes

### 3. Workflow Implementation

The change request system implements the ISO 23386 workflow with:

- Request creation for new properties or changes to existing ones
- Expert review and validation process
- Proper status tracking (draft, candidate, active, deprecated, etc.)
- Full audit trail of all changes

### 4. Data Model Alignment

The data models in PropBench are directly aligned with ISO 23386 concepts:

- `Property` - The core entity representing a property with all required attributes
- `PropertyDictionary` - Collection of properties with versioning
- `PropertyGroup` - Hierarchical organization of properties
- `ChangeRequest` - Implementation of the workflow process
- `AuditLog` - Tracking of all property changes

## Technical Implementation

### Database Schema

The database schema implements all required ISO 23386 attributes for properties:

- Identification attributes (globally unique identifiers)
- Description attributes (names, definitions in multiple languages)
- Technical attributes (data types, units, values)
- Management attributes (status, validity dates, version)
- Relation attributes (connections to other properties)

### Validation Rules

The system enforces ISO 23386 validation rules, including:

- Required fields based on property status
- Data type constraints for property values
- Relationship integrity between properties

### Collaborative Workflow

The workflow system implements the collaborative process required by ISO 23386:

1. Draft creation by regular users
2. Review and validation by experts
3. Activation for use in projects
4. Deprecation and retirement process

## Extensibility

The PropBench implementation is designed to be extensible for future standards:

- Support for ISO 23387 (data templates)
- Integration capability with ISO 12006 (classification systems)
- Compatibility with IFC and other BIM standards
