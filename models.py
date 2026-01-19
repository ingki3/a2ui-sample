from typing import List, Dict, Any, Optional, Union, Literal
from pydantic import BaseModel, Field

# Base Component
class ComponentBase(BaseModel):
    pass

class TextContent(BaseModel):
    literalString: Optional[str] = None
    path: Optional[str] = None

class TextComponent(ComponentBase):
    usageHint: Optional[str] = None
    text: TextContent

class TextFieldComponent(ComponentBase):
    label: TextContent
    text: TextContent

class ActionContext(BaseModel):
    key: str
    value: TextContent

class Action(BaseModel):
    name: str
    context: List[ActionContext] = []

class ButtonComponent(ComponentBase):
    action: Action
    child: str # ID reference to a text component usually

class ColumnChildren(BaseModel):
    explicitList: List[str]

class ColumnComponent(ComponentBase):
    children: ColumnChildren

class ImageComponent(ComponentBase):
    url: TextContent
    altText: Optional[TextContent] = None

class RowComponent(ComponentBase):
    children: ColumnChildren # Reuse ColumnChildren because structure is same (explicitList)

class ChartDataPoint(BaseModel):
    label: str
    value: float

class ChartComponent(ComponentBase):
    data: List[ChartDataPoint]
    color: Optional[str] = "#0F9D58" # Default Google Green

# Union of all possible component types
class ComponentType(BaseModel):
    Text: Optional[TextComponent] = None
    TextField: Optional[TextFieldComponent] = None
    Button: Optional[ButtonComponent] = None
    Column: Optional[ColumnComponent] = None
    Row: Optional[RowComponent] = None
    Image: Optional[ImageComponent] = None
    Chart: Optional[ChartComponent] = None

class ComponentEntry(BaseModel):
    id: str
    component: ComponentType

class SurfaceUpdate(BaseModel):
    surfaceId: str
    components: List[ComponentEntry]

class DataValue(BaseModel):
    key: str
    valueString: str

class DataModelContents(BaseModel):
    key: str # e.g. "calculator"
    valueMap: List[DataValue]

class DataModelUpdate(BaseModel):
    surfaceId: str
    contents: List[DataModelContents]

class BeginRendering(BaseModel):
    surfaceId: str
    root: str

class A2UIData(BaseModel):
    surfaceUpdate: Optional[SurfaceUpdate] = None
    dataModelUpdate: Optional[DataModelUpdate] = None
    beginRendering: Optional[BeginRendering] = None

class A2UIResponse(BaseModel):
    kind: str = "a2ui" # Custom discriminator
    data: A2UIData

class TextResponse(BaseModel):
    kind: str = "text"
    text: str
