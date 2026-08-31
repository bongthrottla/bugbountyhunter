import time
import timeit

def run_test(num_subdomains, num_live_hosts):
    subdomains = [f'sub{i}.example.com' for i in range(num_subdomains)]
    live_hosts_list = [f'sub{i}.example.com' for i in range(num_live_hosts)]

    # List test
    start = time.time()
    for sub in subdomains:
        _ = sub in live_hosts_list
    list_time = time.time() - start

    # Set test
    live_hosts_set = set(live_hosts_list)
    start = time.time()
    for sub in subdomains:
        _ = sub in live_hosts_set
    set_time = time.time() - start

    print(f'Size: {num_subdomains} subdomains, {num_live_hosts} live hosts')
    print(f'List time (baseline): {list_time:.4f}s')
    print(f'Set time (improved):  {set_time:.4f}s')
    if set_time > 0:
        improvement = (list_time / set_time)
        print(f'Improvement: {improvement:.2f}x faster')
        print(f'Reduction in time: {((list_time - set_time)/list_time)*100:.2f}%')
    else:
        print('Set time was near 0.')
    print('-' * 40)

if __name__ == '__main__':
    print('Benchmarking subdomain membership check...\n')
    run_test(1000, 500)
    run_test(10000, 5000)
    run_test(100000, 50000)
