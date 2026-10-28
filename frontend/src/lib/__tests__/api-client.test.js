import { getErrorMessage, handleResponseError } from '../api-client';

describe('getErrorMessage', () => {
  it('says the order was not found on a 404', () => {
    expect(getErrorMessage({ message: 'Request failed with status code 404', response: { status: 404, data: { detail: 'No OrderRecord matches the given query.' } } }))
      .toBe('Order not found.');
  });

  it("uses DRF's detail message", () => {
    expect(getErrorMessage({ message: 'Request failed with status code 400', response: { status: 400, data: { detail: 'Bad lookup.' } } }))
      .toBe('Bad lookup.');
  });

  it('falls back to the error message, then a generic one', () => {
    expect(getErrorMessage({ message: 'Network Error' })).toBe('Network Error');
    expect(getErrorMessage({ response: { status: 500, data: '<html>' } })).toBe('Something went wrong. Please try again.');
  });
});

describe('handleResponseError', () => {
  it('rejects with the same error, its message rewritten', async () => {
    const error = { message: 'Request failed with status code 404', response: { status: 404 } };
    await expect(handleResponseError(error)).rejects.toBe(error);
    expect(error.message).toBe('Order not found.');
  });
});
