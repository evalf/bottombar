from typing import Callable, Protocol, TextIO, ContextManager, TypeVar, Any, Optional, Generic, overload

T0 = TypeVar('T0')
T1 = TypeVar('T1')
T2 = TypeVar('T2')
T3 = TypeVar('T3')
T4 = TypeVar('T4')
T5 = TypeVar('T5')

T0_contra = TypeVar('T0_contra', contravariant=True)
T1_contra = TypeVar('T1_contra', contravariant=True)
T2_contra = TypeVar('T2_contra', contravariant=True)
T3_contra = TypeVar('T3_contra', contravariant=True)
T4_contra = TypeVar('T4_contra', contravariant=True)
T5_contra = TypeVar('T5_contra', contravariant=True)

class F0(Protocol):
  def __call__(self, *,
    width: int) -> str: ...

class F1(Protocol[T0_contra]):
  def __call__(self, __arg0: T0_contra,
    width: int) -> str: ...

class F2(Protocol[T0_contra,T1_contra]):
  def __call__(self, __arg0: T0_contra, __arg1: T1_contra, *,
    width: int) -> str: ...

class F3(Protocol[T0_contra,T1_contra,T2_contra]):
  def __call__(self, __arg0: T0_contra, __arg1: T1_contra, __arg2: T2_contra, *,
    width: int) -> str: ...

class F4(Protocol[T0_contra,T1_contra,T2_contra,T3_contra]):
  def __call__(self, __arg0: T0_contra, __arg1: T1_contra, __arg2: T2_contra, __arg3: T3_contra, *,
    width: int) -> str: ...

class F5(Protocol[T0_contra,T1_contra,T2_contra,T3_contra,T4_contra]):
  def __call__(self, __arg0: T0_contra, __arg1: T1_contra, __arg2: T2_contra, __arg3: T3_contra, __arg4: T4_contra, *,
    width: int) -> str: ...

class F6(Protocol[T0_contra,T1_contra,T2_contra,T3_contra,T4_contra,T5_contra]):
  def __call__(self, __arg0: T0_contra, __arg1: T1_contra, __arg2: T2_contra, __arg3: T3_contra, __arg4: T4_contra, __arg5: T5_contra, *,
    width: int) -> str: ...

class Fany(Protocol):
  def __call__(*args: Any,
    width: int) -> str: ...

@overload
def BottomBar(*,
  format: F0, output: TextIO = ..., interval: Optional[float] = ...) -> ContextManager[Callable[[], None]]: ...

@overload
def BottomBar(__arg0: T0, *,
  format: F1[T0], output: TextIO = ..., interval: Optional[float] = ...) -> ContextManager[Callable[[T0], None]]: ...

@overload
def BottomBar(__arg0: T0, __arg1: T1, *,
  format: F2[T0, T1], output: TextIO = ..., interval: Optional[float] = ...) -> ContextManager[Callable[[T0, T1], None]]: ...

@overload
def BottomBar(__arg0: T0, __arg1: T1, __arg2: T2, *,
  format: F3[T0, T1, T2], output: TextIO = ..., interval: Optional[float] = ...) -> ContextManager[Callable[[T0, T1, T2], None]]: ...

@overload
def BottomBar(__arg0: T0, __arg1: T1, __arg2: T2, __arg3: T3, *,
  format: F4[T0, T1, T2, T3], output: TextIO = ..., interval: Optional[float] = ...) -> ContextManager[Callable[[T0, T1, T2, T3], None]]: ...

@overload
def BottomBar(__arg0: T0, __arg1: T1, __arg2: T2, __arg3: T3, __arg4: T4, *,
  format: F5[T0, T1, T2, T3, T4], output: TextIO = ..., interval: Optional[float] = ...) -> ContextManager[Callable[[T0, T1, T2, T3, T4], None]]: ...

@overload
def BottomBar(__arg0: T0, __arg1: T1, __arg2: T2, __arg3: T3, __arg4: T4, __arg5: T5, *,
  format: F6[T0, T1, T2, T3, T4, T5], output: TextIO = ..., interval: Optional[float] = ...) -> ContextManager[Callable[[T0, T1, T2, T3, T4, T5], None]]: ...

@overload
def BottomBar(*args: Any,
  format: Fany, output: TextIO = ..., interval: Optional[float] = ...) -> ContextManager[Callable[..., None]]: ...

@overload
def BottomBar(*args: Any,
  output: TextIO = ..., interval: Optional[float] = ...) -> ContextManager[Callable[..., None]]: ...

# vim:sw=2:sts=2:et
