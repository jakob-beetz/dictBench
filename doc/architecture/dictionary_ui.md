## Dictionary Switching and Management in the User Interface

To provide a seamless user experience for managing multiple property dictionaries, the PropBench system includes dedicated UI components:

![Dictionary Selector](../images/dictionary_selector.png)

### Key UI Components

1. **Dictionary Selection Dropdown**
   - Located in the main navigation bar
   - Shows currently active dictionary
   - Allows switching between available dictionaries
   - Indicates dictionary status with icons/colors

2. **Dictionary Management Interface**
   - List view of all dictionaries with filters and search
   - Detail view for individual dictionaries
   - Create/Edit dictionary forms
   - Dictionary lifecycle management controls
   - Dictionary statistics dashboard

3. **Property Creation with Dictionary Context**
   - When creating a new property, the active dictionary is automatically assigned
   - Option to select a different dictionary during property creation
   - Visual indicators showing which dictionary a property belongs to

### Dictionary Switching Workflow

1. User selects a different dictionary from the dropdown
2. System confirms the switch and loads the new dictionary context
3. All property-related views are updated to show only properties from the selected dictionary
4. User interface reflects the active dictionary in the header/navigation
5. Dictionary-specific validation rules are activated

### Benefits of Multiple Dictionaries

The multiple dictionary architecture provides several key benefits:

1. **Standards Compliance**: Support for both international and local property standards
2. **Organizational Flexibility**: Different teams can maintain their own specialized dictionaries
3. **Project Isolation**: Project-specific properties can be kept separate from organizational standards
4. **Versioning Support**: New versions of dictionaries can be created while preserving older versions
5. **Interoperability**: Properties can be exchanged between systems while maintaining their context
6. **Customization**: Organizations can extend standard dictionaries with their own properties

### Implementation Example

The dictionary switching functionality is implemented in the frontend using React context:

```javascript
// DictionaryContext.js
import React, { createContext, useState, useEffect } from 'react';
import api from '../services/api';

export const DictionaryContext = createContext();

export const DictionaryProvider = ({ children }) => {
  const [activeDictionary, setActiveDictionary] = useState(null);
  const [dictionaries, setDictionaries] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Load dictionaries when component mounts
    loadDictionaries();
  }, []);

  const loadDictionaries = async () => {
    setLoading(true);
    try {
      const response = await api.get('/dictionaries/');
      setDictionaries(response.data);
      
      // Set active dictionary (either default or first available)
      const defaultDict = response.data.find(dict => dict.is_default);
      setActiveDictionary(defaultDict || response.data[0]);
    } catch (error) {
      console.error('Failed to load dictionaries', error);
    }
    setLoading(false);
  };

  const switchDictionary = async (dictionaryId) => {
    setLoading(true);
    try {
      const dict = dictionaries.find(d => d.guid === dictionaryId);
      if (dict) {
        setActiveDictionary(dict);
        // Set as default on the server
        await api.post(`/dictionaries/${dictionaryId}/set_default/`);
      }
    } catch (error) {
      console.error('Failed to switch dictionary', error);
    }
    setLoading(false);
  };

  return (
    <DictionaryContext.Provider
      value={{
        activeDictionary,
        dictionaries,
        loading,
        switchDictionary,
        refreshDictionaries: loadDictionaries
      }}
    >
      {children}
    </DictionaryContext.Provider>
  );
};
```

The dictionary selector component:

```javascript
// DictionarySelector.js
import React, { useContext } from 'react';
import { DictionaryContext } from '../contexts/DictionaryContext';

const DictionarySelector = () => {
  const { activeDictionary, dictionaries, loading, switchDictionary } = useContext(DictionaryContext);

  if (loading) {
    return <div>Loading dictionaries...</div>;
  }

  const handleChange = (e) => {
    switchDictionary(e.target.value);
  };

  return (
    <div className="dictionary-selector">
      <label htmlFor="dictionary-select">Active Dictionary:</label>
      <select
        id="dictionary-select"
        value={activeDictionary?.guid}
        onChange={handleChange}
        className="form-control"
      >
        {dictionaries.map(dict => (
          <option key={dict.guid} value={dict.guid}>
            {dict.name} v{dict.version} {dict.status !== 'active' ? `(${dict.status})` : ''}
          </option>
        ))}
      </select>
    </div>
  );
};

export default DictionarySelector;
```