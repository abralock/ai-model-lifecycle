package de.terrestris.shoguncore.util.interceptor;

import static org.junit.jupiter.api.Assertions.assertThrows;
import org.junit.jupiter.api.Test;

public class InterceptorExceptionTest {

    private static final String EXCEPTION_MESSAGE = "Shinji!";

    @Test
    public void throw_exception_empty() throws InterceptorException {
        assertThrows(InterceptorException.class, () -> {
            throw new InterceptorException();
        });
    }

    @Test
    public void throw_exception_message() throws InterceptorException {
        assertThrows(InterceptorException.class, () -> {
            throw new InterceptorException(EXCEPTION_MESSAGE);
        });
    }

    @Test
    public void throw_exception_throwable() throws InterceptorException {
        assertThrows(InterceptorException.class, () -> {
            throw new InterceptorException(new Throwable());
        });
    }

    @Test
    public void throw_exception_message_throwable() throws InterceptorException {
        assertThrows(InterceptorException.class, () -> {
            throw new InterceptorException(EXCEPTION_MESSAGE, new Throwable());
        });
    }
}
