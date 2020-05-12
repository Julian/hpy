from .support import HPyTest


class TestNumber(HPyTest):

    def test_unary(self):
        import pytest
        import operator
        for c_name, op in [
                ('Negative', operator.neg),
                ('Positive', operator.pos),
                ('Absolute', abs),
                ('Invert', operator.invert),
                ('Index', operator.index),
                ('Long', int),
                ('Float', float),
                ]:
            mod = self.make_module("""
                HPy_DEF_METH_O(f)
                static HPy f_impl(HPyContext ctx, HPy self, HPy arg)
                {
                    return HPy_%s(ctx, arg);
                }
                @EXPORT(f, HPy_METH_O)
                @INIT
            """ % (c_name,), name='number_'+c_name)
            assert mod.f(-5) == op(-5)
            assert mod.f(6) == op(6)
            try:
                res = op(4.75)
            except Exception as e:
                with pytest.raises(e.__class__):
                    mod.f(4.75)
            else:
                assert mod.f(4.75) == res

    def test_binary(self):
        import operator
        for c_name, op in [
                ('Add', operator.add),
                ('Subtract', operator.sub),
                ('Multiply', operator.mul),
                ('FloorDivide', operator.floordiv),
                ('TrueDivide', operator.truediv),
                ('Remainder', operator.mod),
                ('Divmod', divmod),
                ('Lshift', operator.lshift),
                ('Rshift', operator.rshift),
                ('And', operator.and_),
                ('Xor', operator.xor),
                ('Or', operator.or_),
                ]:
            mod = self.make_module("""
                HPy_DEF_METH_VARARGS(f)
                static HPy f_impl(HPyContext ctx, HPy self,
                                  HPy *args, HPy_ssize_t nargs)
                {
                    HPy a, b;
                    if (!HPyArg_Parse(ctx, args, nargs, "OO", &a, &b))
                        return HPy_NULL;
                    return HPy_%s(ctx, a, b);
                }
                @EXPORT(f, HPy_METH_VARARGS)
                @INIT
            """ % (c_name,), name='number_'+c_name)
            assert mod.f(5, 4) == op(5, 4)
            assert mod.f(6, 3) == op(6, 3)

    def test_power(self):
        mod = self.make_module("""
            HPy_DEF_METH_VARARGS(f)
            static HPy f_impl(HPyContext ctx, HPy self,
                              HPy *args, HPy_ssize_t nargs)
            {
                HPy a, b, c;
                if (!HPyArg_Parse(ctx, args, nargs, "OOO", &a, &b, &c))
                    return HPy_NULL;
                return HPy_Power(ctx, a, b, c);
            }
            @EXPORT(f, HPy_METH_VARARGS)
            @INIT
        """)
        assert mod.f(4, 5, None) == 4 ** 5
        assert mod.f(4, 5, 7) == pow(4, 5, 7)

    def test_matmul(self):
        class Mat:
            def __matmul__(self, other):
                return ('matmul', self, other)
        m1 = Mat()
        m2 = Mat()
        mod = self.make_module("""
            HPy_DEF_METH_VARARGS(f)
            static HPy f_impl(HPyContext ctx, HPy self,
                              HPy *args, HPy_ssize_t nargs)
            {
                HPy a, b;
                if (!HPyArg_Parse(ctx, args, nargs, "OO", &a, &b))
                    return HPy_NULL;
                return HPy_MatrixMultiply(ctx, a, b);
            }
            @EXPORT(f, HPy_METH_VARARGS)
            @INIT
        """)
        assert mod.f(m1, m2) == m1.__matmul__(m2)

    def test_inplace_binary(self):
        import operator
        for c_name, py_name in [
                ('Add', '__iadd__'),
                ('Subtract', '__isub__'),
                ('Multiply', '__imul__'),
                ('FloorDivide', '__ifloordiv__'),
                ('TrueDivide', '__itruediv__'),
                ('Remainder', '__imod__'),
                ('Lshift', '__ilshift__'),
                ('Rshift', '__irshift__'),
                ('And', '__iand__'),
                ('Xor', '__ixor__'),
                ('Or', '__ior__'),
                ]:
            mod = self.make_module("""
                HPy_DEF_METH_VARARGS(f)
                static HPy f_impl(HPyContext ctx, HPy self,
                                  HPy *args, HPy_ssize_t nargs)
                {
                    HPy a, b;
                    if (!HPyArg_Parse(ctx, args, nargs, "OO", &a, &b))
                        return HPy_NULL;
                    return HPy_InPlace%s(ctx, a, b);
                }
                @EXPORT(f, HPy_METH_VARARGS)
                @INIT
            """ % (c_name,), name='number_'+c_name)
            class A:
                def mymethod(self, b):
                    return (py_name, b)
            setattr(A, py_name, A.mymethod)
            assert mod.f(A(), 12.34) == A().mymethod(12.34)

    def test_inplace_power(self):
        mod = self.make_module("""
            HPy_DEF_METH_VARARGS(f)
            static HPy f_impl(HPyContext ctx, HPy self,
                              HPy *args, HPy_ssize_t nargs)
            {
                HPy a, b, c;
                if (!HPyArg_Parse(ctx, args, nargs, "OOO", &a, &b, &c))
                    return HPy_NULL;
                return HPy_InPlacePower(ctx, a, b, c);
            }
            @EXPORT(f, HPy_METH_VARARGS)
            @INIT
        """)
        class A:
            def __ipow__(self, b):
                return ('ipow', b)
        # the behavior of PyNumber_InPlacePower is weird: if __ipow__ is
        # defined, the 3rd arg is always ignored, even if the doc say the
        # opposite
        assert mod.f(A(), 5, None) == A().__ipow__(5)
        assert mod.f(A(), 7, 'hello') == A().__ipow__(7)
        assert mod.f(4, 5, 7) == pow(4, 5, 7)

    def test_inplace_matmul(self):
        class Mat:
            def __imatmul__(self, other):
                return ('imatmul', self, other)
        m1 = Mat()
        m2 = Mat()
        mod = self.make_module("""
            HPy_DEF_METH_VARARGS(f)
            static HPy f_impl(HPyContext ctx, HPy self,
                              HPy *args, HPy_ssize_t nargs)
            {
                HPy a, b;
                if (!HPyArg_Parse(ctx, args, nargs, "OO", &a, &b))
                    return HPy_NULL;
                return HPy_InPlaceMatrixMultiply(ctx, a, b);
            }
            @EXPORT(f, HPy_METH_VARARGS)
            @INIT
        """)
        assert mod.f(m1, m2) == m1.__imatmul__(m2)
